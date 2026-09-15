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

int	*ft_range(int start, int end);

static void	tst(int start, int end)
{
	int	*tab;
	int	len;
	int	i;

	len = (end >= start ? end - start : start - end) + 1;
	printf("ft_range(%d, %d) = ", start, end);
	fflush(stdout);
	tab = ft_range(start, end);
	if (!tab)
	{
		printf("NULL\n");
		return ;
	}
	printf("[");
	for (i = 0; i < len; i++)
		printf("%s%d", i ? ", " : "", tab[i]);
	printf("]\n");
}

int	main(int argc, char **argv)
{
	int	i;
	int	start;

	if (tst_start(argc, argv) == 0)
	{
		tst(1, 3);
		tst(-1, 2);
		tst(0, 0);
		tst(0, -3);
		tst(5, 5);
		tst(-10, -5);
		tst(3, -2);
		tst(-2147483647 - 1, -2147483645);
		return (0);
	}
	for (i = 0; i < 5; i++)
	{
		start = (int)(tst_rand() % 2001) - 1000;
		tst(start, start + (int)(tst_rand() % 121) - 60);
	}
	return (0);
}
