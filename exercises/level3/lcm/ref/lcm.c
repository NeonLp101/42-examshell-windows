unsigned int	lcm(unsigned int a, unsigned int b)
{
	unsigned int	x;
	unsigned int	y;
	unsigned int	tmp;

	if (a == 0 || b == 0)
		return (0);
	x = a;
	y = b;
	while (y)
	{
		tmp = x % y;
		x = y;
		y = tmp;
	}
	return (a / x * b);
}
