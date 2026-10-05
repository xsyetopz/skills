#include "game.h"

void Sound_Init(void)
{
    __asm {
        _emit 0x55
        _emit 0x8B
        _emit 0xEC
    }
    /* remaining 61 bytes are emitted the same way in sound_bytes.inc */
    #include "sound_bytes.inc"
}
