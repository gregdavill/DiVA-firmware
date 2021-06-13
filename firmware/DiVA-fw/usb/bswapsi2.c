
long __bswapsi2(unsigned long a)
{
    unsigned long res = 0;
    res = ((a >> 24) & 0xFF) | ((a >> 8) & 0xFF00) | ((a << 8) & 0xFF0000) | ((a << 24) & 0xFF000000);
    return res;
}