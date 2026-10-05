# Bolt firmware (CH32V003)

One file, [`bolt.c`](bolt.c), on [ch32fun](https://github.com/cnlohr/ch32fun) (its `ch32v00x_touch.h`
for the antenna and `ws2812b_simple.h` for the eyes). The comments at its top say what it does, pin by
pin, and which USB Type-C rules it follows.

## Build

```sh
make build CH32FUN=/path/to/ch32fun/ch32fun PREFIX=/path/to/bin/riscv-none-elf
```

Always name the `build` target: ch32fun's own default target tries to flash a chip.

Compiled on 2026-10-05 with xPack riscv-none-elf-gcc 15.2.0 and ch32fun 6b247c7:

```
Memory region         Used Size  Region Size  %age Used
           FLASH:        2996 B        16 KB     18.29%
             RAM:         500 B         2 KB     24.41%
```

[`bolt.bin`](bolt.bin) and [`bolt.hex`](bolt.hex) are that build. The only compiler warning comes from
ch32fun's touch header (`ReadTouchPinSafe` defined but not used); `bolt.c` itself compiles clean.

## Flash

Three pads (VDD, SWIO, GND) between Bolt's feet take a WCH-LinkE: `make flash CH32FUN=...`
(minichlink). Power the board from the IN foot or from the programmer, not both.

## Status

Compiled, not yet run on hardware: no Bolt has been built. On the first prototypes:
- read the CC ADC counts with a few phones attached (a 5.1k Rd should read about 193 behind 22k and
  85 behind 56k) and with nothing attached (1023);
- check the current reading against a USB power meter at 0.1, 0.5 and 1.5 A;
- tune the antenna's touch threshold (`touch_now`), as on the other touch boards.

## License

MIT (see [`LICENSE`](LICENSE)).
