#include <unistd.h>

int	main(int argc, char **argv)
{
	char	*s;
	int		printed;

	if (argc == 2)
	{
		s = argv[1];
		printed = 0;
		while (*s)
		{
			while (*s == ' ' || *s == '\t')
				s++;
			if (!*s)
				break ;
			if (printed)
				write(1, " ", 1);
			while (*s && *s != ' ' && *s != '\t')
				write(1, s++, 1);
			printed = 1;
		}
	}
	write(1, "\n", 1);
	return (0);
}
