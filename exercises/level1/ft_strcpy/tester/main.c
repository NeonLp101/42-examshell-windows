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

char	*ft_strcpy(char *s1, char *s2);

static void	tst(const char *src)
{
	char	dest[128];
	char	*copy;
	char	*ret;
	size_t	len;

	memset(dest, 'X', sizeof(dest));
	dest[127] = '\0';
	copy = tst_dup(src);
	printf("ft_strcpy(dest, ");
	tst_put_str(src);
	printf(") -> ");
	fflush(stdout);
	ret = ft_strcpy(dest, copy);
	printf("dest = ");
	tst_put_str(dest);
	printf(", returns %s", ret == dest ? "dest" : "something else (must return s1)");
	len = strlen(src);
	if (dest[len + 1] != 'X')
		printf(" !! wrote past the '\\0'");
	printf("\n");
}

int	main(int argc, char **argv)
{
	char	buf[64];
	int		i;

	if (tst_start(argc, argv) == 0)
	{
		tst("");
		tst("a");
		tst("Hello World!");
		tst("tab\tand\nnewline");
		tst("0123456789012345678901234567890123456789");
		return (0);
	}
	for (i = 0; i < 5; i++)
		tst(tst_rand_str(buf, 50, "abcdefXYZ0123 .,!"));
	return (0);
}
