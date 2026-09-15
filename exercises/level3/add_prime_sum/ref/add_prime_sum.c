#include <unistd.h>

static void	put_nbr(long long n)
{
	char	c;

	if (n < 0)
	{
		write(1, "-", 1);
		n = -n;
	}
	if (n >= 10)
		put_nbr(n / 10);
	c = '0' + n % 10;
	write(1, &c, 1);
}

static long long	to_number(const char *s)
{
	long long	n;
	int			sign;

	sign = 1;
	n = 0;
	if (*s == '-' || *s == '+')
		sign = (*s++ == '-') ? -1 : 1;
	while (*s >= '0' && *s <= '9')
		n = n * 10 + (*s++ - '0');
	return (n * sign);
}

static int	is_prime(long long n)
{
	long long	d;

	if (n < 2)
		return (0);
	d = 2;
	while (d * d <= n)
	{
		if (n % d == 0)
			return (0);
		d++;
	}
	return (1);
}

int	main(int argc, char **argv)
{
	long long	n;
	long long	sum;

	sum = 0;
	if (argc == 2)
	{
		n = to_number(argv[1]);
		while (n > 1)
		{
			if (is_prime(n))
				sum += n;
			n--;
		}
	}
	put_nbr(sum);
	write(1, "\n", 1);
	return (0);
}
