#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

static unsigned int	g_seed;

__attribute__((unused))
static unsigned int	tst_rand(void)
{
	g_seed = g_seed * 1103515245u + 12345u;
	return ((g_seed >> 8) & 0xffffff);
}

__attribute__((unused))
static int	tst_start(int argc, char **argv)
{
	int	t;

	t = (argc > 1) ? atoi(argv[1]) : 0;
	g_seed = (unsigned int)t * 2654435761u + 7u;
	return (t);
}

/* prints a C string literal, with escapes, e.g. "a\tb" */
__attribute__((unused))
static void	tst_put_str(const char *s)
{
	if (!s)
	{
		printf("NULL");
		return ;
	}
	putchar('"');
	for (; *s; s++)
	{
		if (*s == '\t')
			printf("\\t");
		else if (*s == '\n')
			printf("\\n");
		else if (*s == '\v')
			printf("\\v");
		else if (*s == '\f')
			printf("\\f");
		else if (*s == '\r')
			printf("\\r");
		else if (*s == '"' || *s == '\\')
			printf("\\%c", *s);
		else
			putchar(*s);
	}
	putchar('"');
}

/* random string of length 0..maxlen made of charset */
__attribute__((unused))
static char	*tst_rand_str(char *buf, int maxlen, const char *charset)
{
	int		len;
	int		i;
	size_t	n;

	len = (int)(tst_rand() % (unsigned int)(maxlen + 1));
	n = strlen(charset);
	for (i = 0; i < len; i++)
		buf[i] = charset[tst_rand() % n];
	buf[len] = '\0';
	return (buf);
}

__attribute__((unused))
static char	*tst_dup(const char *s)
{
	size_t	len;
	char	*d;

	len = strlen(s);
	d = malloc(len + 1);
	memcpy(d, s, len + 1);
	return (d);
}

/* same layout as the ft_list.h required by the subject */
typedef struct s_tst_list
{
	struct s_tst_list	*next;
	void				*data;
}						t_tst_list;

int	ft_list_size(t_tst_list *begin_list);

static void	tst(int n)
{
	t_tst_list	*head;
	t_tst_list	*node;
	int			i;

	head = NULL;
	for (i = 0; i < n; i++)
	{
		node = malloc(sizeof(t_tst_list));
		node->data = NULL;
		node->next = head;
		head = node;
	}
	printf("ft_list_size(list of %d nodes) = ", n);
	fflush(stdout);
	printf("%d\n", ft_list_size(head));
}

int	main(int argc, char **argv)
{
	int	i;

	if (tst_start(argc, argv) == 0)
	{
		tst(0);
		tst(1);
		tst(2);
		tst(10);
		return (0);
	}
	for (i = 0; i < 4; i++)
		tst((int)(tst_rand() % 200));
	return (0);
}
