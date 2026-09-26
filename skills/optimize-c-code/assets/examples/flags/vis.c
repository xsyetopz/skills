/* A shared library with one public entry point. Build it with and
 * without -fvisibility=hidden and count exported symbols with nm -gU. */
#define API __attribute__((visibility("default")))

int vis_helper_a(int x);
int vis_helper_b(int x);
API int vis_api(int x);

int vis_helper_a(int x) { return x * 2; }
int vis_helper_b(int x) { return x + 7; }
API int vis_api(int x) { return vis_helper_a(x) + vis_helper_b(x); }
