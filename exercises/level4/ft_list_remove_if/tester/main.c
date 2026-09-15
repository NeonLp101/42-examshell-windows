#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ft_list.h"

void	ft_list_remove_if(t_list **begin_list, void *data_ref, int (*cmp)());

static unsigned int	g_seed;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static int	cmp_str(void *a, void *b)
{
	return (strcmp((char *)a, (char *)b));
}

static void	tst_print(t_list *node, int max)
{
	int	i;

	printf("[");
	for (i = 0; node && i <= max; node = node->next, i++)
		printf("%s\"%s\"", i ? ", " : "", (char *)node->data);
	printf("]%s", node ? " ...list is longer than it should be (cycle?)" : "");
}

static void	tst(const char **words, int n, const char *ref)
{
	t_list	*head;
	t_list	**cur;
	char	ref_copy[64];
	int		i;

	head = NULL;
	cur = &head;
	for (i = 0; i < n; i++)
	{
		*cur = malloc(sizeof(t_list));
		(*cur)->data = (void *)words[i];
		(*cur)->next = NULL;
		cur = &(*cur)->next;
	}
	/* different pointer, same content: you must use cmp, not == */
	strcpy(ref_copy, ref);
	printf("ft_list_remove_if(");
	tst_print(head, n);
	printf(", \"%s\", cmp) -> ", ref);
	fflush(stdout);
	ft_list_remove_if(&head, ref_copy, cmp_str);
	tst_print(head, n);
	printf("\n");
}

int	main(int argc, char **argv)
{
	static const char	*l1[] = {"a"};
	static const char	*l2[] = {"a", "b", "c"};
	static const char	*l3[] = {"a", "a", "a", "b", "a", "c", "a", "a"};
	static const char	*l4[] = {"x", "x", "x"};
	static const char	*l5[] = {"hello", "world", "hello", "42"};
	static const char	*vocab[] = {"a", "b", "c", "42"};
	const char			*words[32];
	int					t;
	int					i;
	int					j;
	int					n;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		tst(NULL, 0, "a");
		tst(l1, 1, "a");
		tst(l1, 1, "b");
		tst(l2, 3, "a");
		tst(l2, 3, "b");
		tst(l2, 3, "c");
		tst(l2, 3, "z");
		tst(l3, 8, "a");
		tst(l3, 8, "b");
		tst(l4, 3, "x");
		tst(l5, 4, "hello");
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	for (i = 0; i < 4; i++)
	{
		n = (int)(tst_rand() % 16);
		for (j = 0; j < n; j++)
			words[j] = vocab[tst_rand() % 4];
		tst(words, n, vocab[tst_rand() % 4]);
	}
	return (0);
}
