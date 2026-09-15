#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

char	*ft_itoa(int nbr);

static unsigned int	g_seed;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static void	tst(int n)
{
	char	*s;

	printf("ft_itoa(%d) = ", n);
	fflush(stdout);
	s = ft_itoa(n);
	if (!s)
		printf("NULL\n");
	else
		printf("\"%s\"\n", s);
}

int	main(int argc, char **argv)
{
	static const int	fixed[] = {0, 1, -1, 5, -5, 9, 10, -10, 42, -42, 99,
		100, -100, 12345, -98765, 1000000000, -1000000000, 2147483647,
		-2147483647, INT_MIN};
	int					t;
	int					i;
	int					v;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		for (i = 0; i < (int)(sizeof(fixed) / sizeof(*fixed)); i++)
			tst(fixed[i]);
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	for (i = 0; i < 8; i++)
	{
		switch (tst_rand() % 4)
		{
			case 0: v = (int)(tst_rand() % 19) - 9; break ;
			case 1: v = (int)(tst_rand() % 200001) - 100000; break ;
			case 2: v = (int)((tst_rand() << 8) ^ tst_rand()); break ;
			default: v = (tst_rand() % 2) ? INT_MAX - (int)(tst_rand() % 1000)
				: INT_MIN + (int)(tst_rand() % 1000); break ;
		}
		tst(v);
	}
	return (0);
}
