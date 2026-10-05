#include "game.h"

void Player_Update(Player *p, int dt)
{
    int speed = p->speed * dt;

    p->y += p->vy * speed;
    p->x += p->vx * speed;
    if (p->y > FLOOR_Y) {
        p->y = FLOOR_Y;
        p->vy = 0;
    }
}

void Player_Draw(const Player *p)
{
    Blit(p->sprite, p->x >> 4, p->y >> 4);
}
