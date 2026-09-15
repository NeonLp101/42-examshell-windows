#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

void	sort_int_tab(int *tab, unsigned int size);

static unsigned int	g_seed;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static void	tst_print(const int *tab, unsigned int size)
{
	unsigned int	i;

	printf("[");
	for (i = 0; i < size; i++)
		printf("%s%d", i ? ", " : "", tab[i]);
	printf("]");
}

static void	tst(const int *src, unsigned int size)
{
	int				*tab;
	unsigned int	i;

	tab = malloc(sizeof(int) * (size + 2));
	for (i = 0; i < size; i++)
		tab[i] = src[i];
	tab[size] = INT_MIN;
	tab[size + 1] = INT_MIN;
	printf("sort_int_tab(");
	tst_print(tab, size);
	printf(", %u) -> ", size);
	fflush(stdout);
	sort_int_tab(tab, size);
	tst_print(tab, size);
	printf("\n");
	if (tab[size] != INT_MIN || tab[size + 1] != INT_MIN)
		printf("  !! memory after the end of the array was modified\n");
	free(tab);
}

int	main(int argc, char **argv)
{
	static const int	a1[] = {42};
	static const int	a2[] = {2, 1};
	static const int	a3[] = {1, 2};
	static const int	a4[] = {1, 2, 3, 4, 5};
	static const int	a5[] = {5, 4, 3, 2, 1};
	static const int	a6[] = {3, 3, 3};
	static const int	a7[] = {4, 2, 4, 2, 1, 1, 4};
	static const int	a8[] = {-5, 10, 0, INT_MIN, INT_MAX, 7, -1};
	static const int	a9[] = {INT_MAX, INT_MIN};
	static const int	a10[] = {0, -1, 0, 1, 0, -1};
	static const int	a11[] = {10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, -1};
	int					tab[64];
	int					t;
	int					i;
	int					j;
	int					size;
	int					range;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		tst(a1, 1);
		tst(a2, 2);
		tst(a3, 2);
		tst(a4, 5);
		tst(a5, 5);
		tst(a6, 3);
		tst(a7, 7);
		tst(a8, 7);
		tst(a9, 2);
		tst(a10, 6);
		tst(a11, 12);
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	for (i = 0; i < 5; i++)
	{
		size = 1 + (int)(tst_rand() % 40);
		range = (int)(tst_rand() % 3);
		for (j = 0; j < size; j++)
		{
			if (range == 0)
				tab[j] = (int)(tst_rand() % 10);
			else if (range == 1)
				tab[j] = (int)(tst_rand() % 2001) - 1000;
			else
				tab[j] = (int)((tst_rand() << 8) ^ tst_rand());
		}
		tst(tab, (unsigned int)size);
	}
	return (0);
}
