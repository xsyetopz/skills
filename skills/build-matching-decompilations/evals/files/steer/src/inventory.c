#include "game.h"

int Inventory_Add(Inventory *inv, int item)
{
    int i;
    Slot *slot;

    for (i = 0; i <= inv->count; i++) {
        slot = &inv->slots[i];
        if (slot->item == item) {
            slot->qty += 1;
            return i;
        }
    }
    return -1;
}
