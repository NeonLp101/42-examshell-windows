#include <unistd.h>

static int	is_blank(char c)
{
	return (c == ' ' || c == '\t' || c == '\0');
}

int	main(int argc, char **argv)
{
	int		i;
	int		j;
	char	c;

	i = 1;
	while (i < argc)
	{
		j = 0;
		while (argv[i][j])
		{
			c = argv[i][j];
			if (c >= 'A' && c <= 'Z')
				c += 32;
			if (c >= 'a' && c <= 'z' && (j == 0 || is_blank(argv[i][j - 1])))
				c -= 32;
			write(1, &c, 1);
			j++;
		}
		write(1, "\n", 1);
		i++;
	}
	if (argc < 2)
		write(1, "\n", 1);
	return (0);
}
