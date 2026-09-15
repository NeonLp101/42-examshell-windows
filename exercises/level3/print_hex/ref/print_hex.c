#include <unistd.h>

static void	put_hex(unsigned long long n)
{
	if (n >= 16)
		put_hex(n / 16);
	write(1, &"0123456789abcdef"[n % 16], 1);
}

int	main(int argc, char **argv)
{
	unsigned long long	n;
	char				*s;

	if (argc == 2)
	{
		n = 0;
		s = argv[1];
		while (*s >= '0' && *s <= '9')
			n = n * 10 + (*s++ - '0');
		put_hex(n);
	}
	write(1, "\n", 1);
	return (0);
}
