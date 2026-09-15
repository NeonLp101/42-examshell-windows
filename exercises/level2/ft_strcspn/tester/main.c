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

size_t	ft_strcspn(const char *s, const char *set);

static void	tst(const char *s, const char *set)
{
	printf("ft_strcspn(");
	tst_put_str(s);
	printf(", ");
	tst_put_str(set);
	printf(") = ");
	fflush(stdout);
	printf("%u\n", (unsigned int)ft_strcspn(s, set));
}

int	main(int argc, char **argv)
{
	char	a[32];
	char	b[16];
	int		i;

	if (tst_start(argc, argv) == 0)
	{
		tst("hello", "l");
		tst("hello", "");
		tst("", "abc");
		tst("", "");
		tst("hello", "xyz");
		tst("hello", "oh");
		tst("abc\tdef", "\t");
		tst("hello world", " ");
		return (0);
	}
	for (i = 0; i < 8; i++)
		tst(tst_rand_str(a, 12, "abcdef"), tst_rand_str(b, 3, "abcdefxyz"));
	return (0);
}
