static int	digit_value(char c)
{
	if (c >= '0' && c <= '9')
		return (c - '0');
	if (c >= 'a' && c <= 'f')
		return (c - 'a' + 10);
	if (c >= 'A' && c <= 'F')
		return (c - 'A' + 10);
	return (-1);
}

int	ft_atoi_base(const char *str, int str_base)
{
	int	result;
	int	sign;
	int	d;

	result = 0;
	sign = 1;
	if (*str == '-')
	{
		sign = -1;
		str++;
	}
	while (*str)
	{
		d = digit_value(*str);
		if (d < 0 || d >= str_base)
			break ;
		result = result * str_base + d;
		str++;
	}
	return (result * sign);
}
