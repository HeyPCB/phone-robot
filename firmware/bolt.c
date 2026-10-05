/*
 * Bolt, the phone stand robot - firmware for the CH32V003 (heypcb.ai merch 09), on ch32fun.
 *
 * What it does
 *   - Left foot (J1) is a USB-C sink: 5.1k Rd on both CC lines, so any USB-C charger gives it 5 V. The MCU
 *     reads those CC lines to learn what the charger offers (default USB, 1.5 A or 3 A).
 *   - Right foot (J2) is a USB-C source for the phone. It offers what the charger can give, capped at
 *     1.5 A (the P-FET's heat): 22k Rp from RP_15 for 1.5 A, 56k Rp from RP_DEF for default USB power.
 *   - VBUS to the phone is off until the MCU sees a phone's 5.1k Rd on one CC line for 150 ms (the
 *     USB-C attach debounce); then the P-FET switch turns on (soft start in hardware). When the Rd goes
 *     away for 20 ms it switches off, and a 10k bleeder empties the port. Rd on both lines (a debug
 *     accessory) or Ra on both (an audio adapter) never gets VBUS. No USB Power Delivery: 5 V only.
 *   - Charge current through the 20 mOhm shunt, INA180A2 gain 50: 1 V per amp, read by the ADC every
 *     10 ms and averaged over a second. Over 1.8 A (1.5 A offered) or 1.1 A (default offered) for half a
 *     second, or over 3 A twice in a row, the port switches off and the eyes go red; it tries again 5 s
 *     later.
 *   - The eyes (two WS2812C) show it over the top of the phone:
 *       no phone           soft blue, a blink every few seconds
 *       eating (>300 mA)   orange, pulsing faster the more it draws
 *       sipping (60-300)   yellow-green
 *       full (<60 mA, 1 min)  green; dims after 5 minutes
 *       fault              red, blinking
 *     The current is the phone's own charge current, so "full" means the phone stopped charging
 *     (full, or holding at its own 80 % limit).
 *   - The gold antenna is a capacitive touch pad: a tap switches night mode (eyes off; a tap in night
 *     mode shows the status for 3 s). A fault still blinks, dimly.
 *
 * Pins (from the board's netlist; KiCad symbol MCU_WCH_RiscV:CH32V003FxPx)
 *   PA2 (pin 6)  OUT_CC1   ADC ch 0      PA1 (pin 5)  OUT_CC2   ADC ch 1
 *   PD2 (pin 19) IN_CC1    ADC ch 3      PD3 (pin 20) IN_CC2    ADC ch 4
 *   PD4 (pin 1)  ISENSE    ADC ch 7      PD6 (pin 3)  TOUCH     ADC ch 6, the antenna through 1k
 *   PC1 (pin 11) RP_15     22k Rp drive  PC2 (pin 12) RP_DEF    56k Rp drive
 *   PC3 (pin 13) VBUS_EN   N-FET gate (high = phone port on)
 *   PC6 (pin 16) LED_DIN   the two WS2812C eyes, left then right
 *   PD1 (pin 18) SWIO      programming
 *
 * The MCU runs from VBUS (5 V nominal). CC readings are ratios of that rail, so they do not care what
 * the charger's voltage is; the current reading assumes 5.0 V and is within the charger's tolerance
 * (about 5 %), which is plenty for a face.
 *
 * Build: make build CH32FUN=... PREFIX=...   (see README.md; always name a target)
 */
#include "ch32fun.h"
#include "ch32v00x_touch.h"
#define WS2812BSIMPLE_IMPLEMENTATION
#include "ws2812b_simple.h"

#define PIN_RP15 PC1
#define PIN_RPDEF PC2
#define PIN_EN PC3
#define PIN_LED PC6

#define CH_OUT_CC1 0
#define CH_OUT_CC2 1
#define CH_IN_CC1 3
#define CH_IN_CC2 4
#define CH_TOUCH 6
#define CH_ISENSE 7

#define MA_PER_COUNT_X100 489         /* 5000 mV / 1023 counts / (1 V per A) = 4.89 mA per count */
#define BRIGHT 48                     /* of 255 */

volatile uint32_t ms;
void SysTick_Handler(void) __attribute__((interrupt));
void SysTick_Handler(void)
{
    SysTick->CMP += DELAY_MS_TIME;
    SysTick->SR = 0;
    ms++;
}

static void systick_init(void)
{
    SysTick->CTLR = 0;
    SysTick->CMP = DELAY_MS_TIME - 1;
    SysTick->CNT = 0;
    SysTick->CTLR = SYSTICK_CTLR_STE | SYSTICK_CTLR_STIE | SYSTICK_CTLR_STCLK;
    NVIC_EnableIRQ(SysTick_IRQn);
}

/* One 10-bit conversion at the longest sample time (241 ADC clocks: the CC lines are 5k sources).
 * ReadTouchPin rewrites SAMPTR2 for its own channel, so set ours every time. */
static uint16_t adc_read(uint8_t ch)
{
    ADC1->RSQR3 = ch;
    ADC1->SAMPTR2 = (ADC1->SAMPTR2 & ~(7u << (3 * ch))) | (7u << (3 * ch));
    ADC1->CTLR2 |= ADC_SWSTART;
    while (!(ADC1->STATR & ADC_EOC))
        ;
    return ADC1->RDATAR & 0x3ff;
}

/* ---- USB-C: what the charger offers, what the phone port sees ---- */
enum offer { OFFER_DEFAULT, OFFER_15 };
enum cc { CC_OPEN, CC_RD, CC_RA };

/* The charger's Rp seen across our 5.1k Rd (USB Type-C vRd ranges, in ADC counts at 5 V): the live
 * line is the higher one; a reading over 2.2 V is not an Rd voltage (VCONN on the other line). */
static enum offer charger_offer(void)
{
    uint16_t a = adc_read(CH_IN_CC1), b = adc_read(CH_IN_CC2), v = 0;
    if (a < 450 && a > v)
        v = a;
    if (b < 450 && b > v)
        v = b;
    return v >= 133 ? OFFER_15 : OFFER_DEFAULT;       /* >= 0.65 V: 1.5 A or 3 A offered */
}

static enum offer offered;
static void set_offer(enum offer o)
{
    offered = o;
    if (o == OFFER_15) {
        funPinMode(PIN_RPDEF, GPIO_CNF_IN_FLOATING);
        funDigitalWrite(PIN_RP15, FUN_HIGH);
        funPinMode(PIN_RP15, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    } else {
        funPinMode(PIN_RP15, GPIO_CNF_IN_FLOATING);
        funDigitalWrite(PIN_RPDEF, FUN_HIGH);
        funPinMode(PIN_RPDEF, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    }
}

/* One CC line of the phone port, against our Rp: Rd 5.1k reads 0.188 of the rail behind 22k, 0.084
 * behind 56k; Ra 1k reads 0.043 / 0.018; open reads the rail. */
static enum cc classify(uint16_t v)
{
    uint16_t rd_lo = offered == OFFER_15 ? 120 : 55, rd_hi = offered == OFFER_15 ? 300 : 150;
    if (v >= rd_lo && v <= rd_hi)
        return CC_RD;
    if (v < rd_lo)
        return CC_RA;
    return CC_OPEN;
}

/* A sink on the port: Rd on exactly one line (the other open, or Ra from a powered cable). */
static int sink_present(void)
{
    enum cc a = classify(adc_read(CH_OUT_CC1)), b = classify(adc_read(CH_OUT_CC2));
    return (a == CC_RD) != (b == CC_RD);
}

static void port_power(int on) { funDigitalWrite(PIN_EN, on ? FUN_HIGH : FUN_LOW); }

/* ---- the eyes ---- */
static void eyes(uint8_t r, uint8_t g, uint8_t b)
{
    uint8_t d[6] = { g, r, b, g, r, b };   /* WS2812: G, R, B per pixel */
    WS2812BSimpleSend(GPIOC, 6, d, 6);
}

static uint8_t scale(uint8_t c, uint16_t level) { return (uint8_t)(((uint16_t)c * level) >> 8); }

/* ---- the antenna ---- */
static uint32_t touch_base;
static int touch_now(void)
{
    uint32_t v = ReadTouchPin(GPIOD, 6, CH_TOUCH, 3);
    if (v > touch_base + touch_base / 16 + 20)       /* tune on hardware */
        return 1;
    touch_base = (touch_base * 15 + v) / 16;
    return 0;
}

enum state { NO_PHONE, ATTACHING, CHARGING, FAULT };

int main(void)
{
    SystemInit();
    funGpioInitAll();
    RCC->APB2PCENR |= RCC_APB2Periph_ADC1;
    static const uint8_t unused[] = { PD5, PD0, PC0, PC4, PC5, PC7 };
    for (unsigned i = 0; i < sizeof unused; i++) {
        funPinMode(unused[i], GPIO_CNF_IN_PUPD);
        funDigitalWrite(unused[i], FUN_HIGH);
    }
    funDigitalWrite(PIN_EN, FUN_LOW);
    funPinMode(PIN_EN, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    funPinMode(PIN_LED, GPIO_Speed_10MHz | GPIO_CNF_OUT_PP);
    static const uint8_t analog[] = { PA2, PA1, PD2, PD3, PD4 };
    for (unsigned i = 0; i < sizeof analog; i++)
        funPinMode(analog[i], GPIO_CNF_IN_ANALOG);
    systick_init();
    InitTouchADC();
    for (int i = 0; i < 16; i++)
        touch_base += ReadTouchPin(GPIOD, 6, CH_TOUCH, 3);
    touch_base /= 16;
    set_offer(charger_offer());
    eyes(0, 0, BRIGHT);                            /* hello */
    Delay_Ms(300);

    enum state st = NO_PHONE;
    uint32_t since = ms, last = ms, low_since = 0, show_until = 0;
    uint32_t sum_ma = 0, avg_ma = 0, over_ms = 0;
    uint16_t n = 0, spikes = 0;
    uint8_t gone = 0;                              /* 10 ms reads in a row without the phone's Rd */
    int night = 0, was_touched = 0;
    for (;;) {
        while (ms - last < 10)
            ;
        last += 10;
        uint32_t now = ms;

        /* the antenna: a tap toggles night mode, or in night mode shows the status for 3 s */
        int t = touch_now();
        if (t && !was_touched) {
            if (night && now < show_until)
                night = 0;
            else if (!night)
                night = 1;
            show_until = now + 3000;
        }
        was_touched = t;

        switch (st) {
        case NO_PHONE:
            if ((now - since) % 1000 < 10)         /* follow the charger once a second */
                set_offer(charger_offer());
            if (sink_present()) {
                st = ATTACHING;
                since = now;
            }
            break;
        case ATTACHING:                            /* tCCDebounce: 150 ms of Rd before VBUS */
            if (!sink_present()) {
                st = NO_PHONE;
                since = now;
            } else if (now - since >= 150) {
                port_power(1);
                st = CHARGING;
                since = now;
                sum_ma = avg_ma = over_ms = 0;
                n = spikes = 0;
                low_since = 0;
                gone = 0;
            }
            break;
        case CHARGING: {
            gone = sink_present() ? 0 : gone + 1;
            uint32_t ma = (uint32_t)adc_read(CH_ISENSE) * MA_PER_COUNT_X100 / 100;
            spikes = ma > 3000 ? spikes + 1 : 0;
            uint32_t limit = offered == OFFER_15 ? 1800 : 1100;
            over_ms = ma > limit ? over_ms + 10 : 0;
            if (gone >= 2) {                       /* the phone left: off within 20 ms */
                port_power(0);
                st = NO_PHONE;
                since = now;
                break;
            }
            if (spikes >= 2 || over_ms >= 500) {
                port_power(0);
                st = FAULT;
                since = now;
                break;
            }
            sum_ma += ma;
            if (++n == 100) {                      /* a one-second average */
                avg_ma = sum_ma / 100;
                sum_ma = 0;
                n = 0;
                if (avg_ma < 60) {
                    if (!low_since)
                        low_since = now;
                } else {
                    low_since = 0;
                }
            }
            break;
        }
        case FAULT:
            if (now - since >= 5000) {             /* try again */
                st = NO_PHONE;
                since = now;
            }
            break;
        }

        /* the face, 50 frames a second */
        if (now % 20 >= 10)
            continue;
        int awake = !night || now < show_until;
        uint16_t phase = (uint16_t)(now % 2000);
        uint16_t tri = phase < 1000 ? phase : 2000 - phase;            /* 0..1000..0 */
        if (st == FAULT) {
            uint8_t on = (now / 250) & 1;
            eyes(on ? (awake ? BRIGHT : BRIGHT / 6) : 0, 0, 0);
        } else if (!awake) {
            eyes(0, 0, 0);
        } else if (st == NO_PHONE || st == ATTACHING) {
            int blink = (now % 4000) > 3850;
            eyes(0, blink ? 0 : BRIGHT / 4, blink ? 0 : BRIGHT);
        } else if (avg_ma > 300 || (avg_ma == 0 && now - since < 1000)) {
            /* eating: a pulse whose speed follows the current, 0.3 to 1.5 A */
            uint32_t period = 2400 - (avg_ma > 1500 ? 1500 : avg_ma);
            uint16_t p = (uint16_t)(now % period), h = (uint16_t)(period / 2);
            uint16_t lv = 128 + (uint16_t)(127u * (p < h ? p : period - p) / h);
            eyes(scale(BRIGHT, lv), scale(BRIGHT * 2 / 5, lv), 0);
        } else if (low_since && now - low_since >= 60000) {
            uint16_t lv = (now - low_since >= 360000) ? 64 : 256;     /* full; dims after 5 more minutes */
            eyes(0, scale(BRIGHT, lv > 255 ? 255 : lv), 0);
        } else {
            uint16_t lv = 160 + tri * 95 / 1000;                       /* sipping: a slow breath */
            eyes(scale(BRIGHT / 2, lv), scale(BRIGHT, lv), 0);
        }
    }
}
