/* Link check only. Never execute this firmware on the laptop or a board. */
extern unsigned long long __udivdi3(unsigned long long, unsigned long long);
volatile unsigned long long numerator = 123456789123ULL, denominator = 37;
void _start(void)
{
    numerator = __udivdi3(numerator, denominator);
    for (;;) {}
}
