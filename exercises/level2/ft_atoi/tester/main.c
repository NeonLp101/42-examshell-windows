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

int	ft_atoi(const char *str);

static void	tst(const char *s)
{
	printf("ft_atoi(");
	tst_put_str(s);
	printf(") = ");
	fflush(stdout);
	printf("%d\n", ft_atoi(s));
}

int	main(int argc, char **argv)
{
	static const char	*fixed[] = {"42", "-42", "+17", "0", "-0", "   123", "\t\n\v\f\r 99",
		"123abc", "abc123", "", "   ", "--5", "+-5", "-+5", " - 5", "0042", "2147483647",
		"-2147483648", "12 34", "-", "+"};
	char				buf[64];
	int					i;
	int					j;
	int					n;

	if (tst_start(argc, argv) == 0)
	{
		for (i = 0; i < (int)(sizeof(fixed) / sizeof(*fixed)); i++)
			tst(fixed[i]);
		return (0);
	}
	for (i = 0; i < 6; i++)
	{
		n = 0;
		for (j = (int)(tst_rand() % 4); j > 0; j--)
			buf[n++] = " \t\n\v\f\r"[tst_rand() % 6];
		j = (int)(tst_rand() % 5);
		if (j == 1)
			buf[n++] = '-';
		else if (j == 2)
			buf[n++] = '+';
		for (j = 1 + (int)(tst_rand() % 9); j > 0; j--)
			buf[n++] = (char)('0' + tst_rand() % 10);
		for (j = (int)(tst_rand() % 3); j > 0; j--)
			buf[n++] = "x -+9 "[tst_rand() % 6];
		buf[n] = '\0';
		tst(buf);
	}
	return (0);
}
