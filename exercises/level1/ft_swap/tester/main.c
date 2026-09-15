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

void	ft_swap(int *a, int *b);

static void	tst(int a, int b)
{
	int	x;
	int	y;

	x = a;
	y = b;
	printf("ft_swap(&a, &b) with a = %d, b = %d -> ", a, b);
	fflush(stdout);
	ft_swap(&x, &y);
	printf("a = %d, b = %d\n", x, y);
}

int	main(int argc, char **argv)
{
	int	i;

	if (tst_start(argc, argv) == 0)
	{
		tst(1, 2);
		tst(42, 42);
		tst(0, -1);
		tst(INT_MIN, INT_MAX);
		tst(-7, 7);
		return (0);
	}
	for (i = 0; i < 5; i++)
		tst((int)((tst_rand() << 8) ^ tst_rand()), (int)((tst_rand() << 8) ^ tst_rand()));
	return (0);
}
