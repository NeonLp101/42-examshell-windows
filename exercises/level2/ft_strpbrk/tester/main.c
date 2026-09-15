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

char	*ft_strpbrk(const char *s1, const char *s2);

static void	tst(const char *s1, const char *s2)
{
	char	*r;

	printf("ft_strpbrk(");
	tst_put_str(s1);
	printf(", ");
	tst_put_str(s2);
	printf(") = ");
	fflush(stdout);
	r = ft_strpbrk(s1, s2);
	if (r == NULL)
		printf("NULL\n");
	else if (r >= s1 && r <= s1 + strlen(s1))
	{
		printf("s1 + %d (", (int)(r - s1));
		tst_put_str(r);
		printf(")\n");
	}
	else
		printf("a pointer outside of s1\n");
}

int	main(int argc, char **argv)
{
	char	a[32];
	char	b[16];
	int		i;

	if (tst_start(argc, argv) == 0)
	{
		tst("hello", "l");
		tst("hello", "xyz");
		tst("", "a");
		tst("hello", "");
		tst("", "");
		tst("abc", "cba");
		tst("hello world", " w");
		return (0);
	}
	for (i = 0; i < 8; i++)
		tst(tst_rand_str(a, 12, "abcdef"), tst_rand_str(b, 3, "abcdefxyz"));
	return (0);
}
