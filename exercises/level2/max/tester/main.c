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

int	max(int *tab, unsigned int len);

static void	tst(const int *src, unsigned int len)
{
	int				tab[64];
	unsigned int	i;

	for (i = 0; i < 64; i++)
		tab[i] = 42;
	printf("max([");
	for (i = 0; i < len; i++)
	{
		tab[i] = src[i];
		printf("%s%d", i ? ", " : "", src[i]);
	}
	printf("], %u) = ", len);
	fflush(stdout);
	printf("%d\n", max(tab, len));
}

int	main(int argc, char **argv)
{
	static const int	a1[] = {42};
	static const int	a2[] = {1, 5, 3};
	static const int	a3[] = {-5, -3, -10};
	static const int	a4[] = {INT_MIN};
	static const int	a5[] = {INT_MIN, INT_MAX, 0};
	static const int	a6[] = {7, 7, 7, 7};
	static const int	a7[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 100};
	int					tab[64];
	int					i;
	int					j;
	int					len;

	if (tst_start(argc, argv) == 0)
	{
		tst(a1, 0);
		tst(a1, 1);
		tst(a2, 3);
		tst(a3, 3);
		tst(a4, 1);
		tst(a5, 3);
		tst(a6, 4);
		tst(a7, 10);
		return (0);
	}
	for (i = 0; i < 5; i++)
	{
		len = 1 + (int)(tst_rand() % 30);
		for (j = 0; j < len; j++)
			tab[j] = (tst_rand() % 2) ? (int)(tst_rand() % 2001) - 1000 : (int)((tst_rand() << 8) ^ tst_rand());
		tst(tab, (unsigned int)len);
	}
	return (0);
}
