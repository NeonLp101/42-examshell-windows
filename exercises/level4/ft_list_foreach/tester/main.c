#include <stdio.h>
#include <stdlib.h>

/* Same layout as the ft_list.h required by the subject. */
typedef struct s_tst_list
{
	struct s_tst_list	*next;
	void				*data;
}						t_tst_list;

void	ft_list_foreach(t_tst_list *begin_list, void (*f)(void *));

static unsigned int	g_seed;
static int			g_calls;

static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

static t_tst_list	*tst_push_back(t_tst_list **head, void *data)
{
	t_tst_list	*node;
	t_tst_list	**cur;

	node = malloc(sizeof(t_tst_list));
	node->data = data;
	node->next = NULL;
	cur = head;
	while (*cur)
		cur = &(*cur)->next;
	*cur = node;
	return (node);
}

static void	print_str(void *data)
{
	printf("  call #%d: f(\"%s\")\n", ++g_calls, (char *)data);
}

static void	add_ten(void *data)
{
	*(int *)data += 10;
	g_calls++;
}

static void	tst_strings(const char **words, int n)
{
	t_tst_list	*head;
	int			i;

	head = NULL;
	for (i = 0; i < n; i++)
		tst_push_back(&head, (void *)words[i]);
	printf("ft_list_foreach(list of %d strings, print_str):\n", n);
	fflush(stdout);
	g_calls = 0;
	ft_list_foreach(head, print_str);
	printf("  -> f was called %d time(s)\n", g_calls);
}

static void	tst_ints(int *values, int n)
{
	t_tst_list	*head;
	t_tst_list	*node;
	int			i;

	head = NULL;
	for (i = 0; i < n; i++)
		tst_push_back(&head, &values[i]);
	printf("ft_list_foreach(list of %d ints, add_ten) -> ", n);
	fflush(stdout);
	g_calls = 0;
	ft_list_foreach(head, add_ten);
	printf("[");
	for (node = head, i = 0; node; node = node->next, i++)
		printf("%s%d", i ? ", " : "", *(int *)node->data);
	printf("] (f called %d time(s))\n", g_calls);
}

int	main(int argc, char **argv)
{
	static const char	*w1[] = {"42"};
	static const char	*w2[] = {"hello", "world", "", "foo bar", "!"};
	static const char	*vocab[] = {"a", "bb", "ccc", "exam", "rank", "02",
		"level", "four", "list", "node"};
	const char			*words[40];
	int					ints[40];
	int					t;
	int					i;
	int					n;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	if (t == 0)
	{
		printf("ft_list_foreach(NULL, print_str):\n");
		fflush(stdout);
		g_calls = 0;
		ft_list_foreach(NULL, print_str);
		printf("  -> f was called %d time(s)\n", g_calls);
		tst_strings(w1, 1);
		tst_strings(w2, 5);
		for (i = 0; i < 6; i++)
			ints[i] = i * 7 - 10;
		tst_ints(ints, 6);
		return (0);
	}
	g_seed = (unsigned int)t * 2654435761u;
	n = 1 + (int)(tst_rand() % 20);
	for (i = 0; i < n; i++)
		words[i] = vocab[tst_rand() % 10];
	tst_strings(words, n);
	n = 1 + (int)(tst_rand() % 40);
	for (i = 0; i < n; i++)
		ints[i] = (int)(tst_rand() % 2001) - 1000;
	tst_ints(ints, n);
	return (0);
}
