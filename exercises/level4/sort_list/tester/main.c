#include <stdio.h>
#include <stdlib.h>
#include <limits.h>
#include "list.h"

t_list	*sort_list(t_list *lst, int (*cmp)(int, int));

static unsigned int	g_seed;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static int	ascending(int a, int b)
{
	return (a <= b);
}

static int	descending(int a, int b)
{
	return (a >= b);
}

static void	tst(const int *src, int size, int asc)
{
	t_list	*head;
	t_list	*node;
	int		i;

	head = NULL;
	for (i = size - 1; i >= 0; i--)
	{
		node = malloc(sizeof(t_list));
		node->data = src[i];
		node->next = head;
		head = node;
	}
	printf("sort_list([");
	for (i = 0; i < size; i++)
		printf("%s%d", i ? ", " : "", src[i]);
	printf("], %s) -> ", asc ? "ascending" : "descending");
	fflush(stdout);
	head = sort_list(head, asc ? ascending : descending);
	printf("[");
	for (i = 0, node = head; node && i <= size; node = node->next, i++)
		printf("%s%d", i ? ", " : "", node->data);
	printf("]%s\n", node ? " ...list is longer than it should be (cycle?)" : "");
}

int	main(int argc, char **argv)
{
	static const int	a1[] = {42};
	static const int	a2[] = {2, 1};
	static const int	a3[] = {1, 2};
	static const int	a4[] = {1, 2, 3, 4, 5};
	static const int	a5[] = {5, 4, 3, 2, 1};
	static const int	a6[] = {7, 7, 7, 7};
	static const int	a7[] = {3, -1, 3, 0, -1, 8, 0};
	static const int	a8[] = {INT_MAX, 0, INT_MIN, -42, 42};
	int					tab[64];
	int					t;
	int					i;
	int					j;
	int					size;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		tst(a1, 1, 1);
		tst(a2, 2, 1);
		tst(a3, 2, 1);
		tst(a4, 5, 1);
		tst(a5, 5, 1);
		tst(a4, 5, 0);
		tst(a6, 4, 1);
		tst(a7, 7, 1);
		tst(a7, 7, 0);
		tst(a8, 5, 1);
		tst(a8, 5, 0);
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	for (i = 0; i < 5; i++)
	{
		size = 1 + (int)(tst_rand() % 30);
		for (j = 0; j < size; j++)
			tab[j] = (tst_rand() % 2) ? (int)(tst_rand() % 10)
				: (int)(tst_rand() % 2001) - 1000;
		tst(tab, size, (int)(tst_rand() % 2));
	}
	return (0);
}
