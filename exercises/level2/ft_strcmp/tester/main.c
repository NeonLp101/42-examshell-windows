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

int	ft_strcmp(char *s1, char *s2);

static void	tst(const char *a, const char *b)
{
	int	r;

	printf("ft_strcmp(");
	tst_put_str(a);
	printf(", ");
	tst_put_str(b);
	printf(") is ");
	fflush(stdout);
	r = ft_strcmp(tst_dup(a), tst_dup(b));
	printf("%s\n", r < 0 ? "negative" : r > 0 ? "positive" : "zero");
}

int	main(int argc, char **argv)
{
	char	a[16];
	char	b[16];
	int		i;

	if (tst_start(argc, argv) == 0)
	{
		tst("", "");
		tst("a", "");
		tst("", "a");
		tst("abc", "abc");
		tst("abc", "abd");
		tst("abd", "abc");
		tst("abc", "abcd");
		tst("abcd", "abc");
		tst("Hello", "hello");
		tst("a\tb", "a b");
		return (0);
	}
	for (i = 0; i < 8; i++)
		tst(tst_rand_str(a, 4, "abc"), tst_rand_str(b, 4, "abc"));
	return (0);
}
