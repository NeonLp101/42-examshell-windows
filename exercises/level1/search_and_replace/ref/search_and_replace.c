#include <unistd.h>

int	main(int argc, char **argv)
{
	char	*s;

	if (argc == 4 && argv[2][0] && !argv[2][1] && argv[3][0] && !argv[3][1])
	{
		s = argv[1];
		while (*s)
		{
			if (*s == argv[2][0])
				write(1, argv[3], 1);
			else
				write(1, s, 1);
			s++;
		}
	}
	write(1, "\n", 1);
	return (0);
}
