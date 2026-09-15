#include <unistd.h>

int	main(int argc, char **argv)
{
	int		seen[256];
	int		i;
	int		j;
	unsigned char	c;

	if (argc == 3)
	{
		i = 0;
		while (i < 256)
			seen[i++] = 0;
		i = 1;
		while (i <= 2)
		{
			j = 0;
			while (argv[i][j])
			{
				c = (unsigned char)argv[i][j];
				if (!seen[c])
				{
					seen[c] = 1;
					write(1, &argv[i][j], 1);
				}
				j++;
			}
			i++;
		}
	}
	write(1, "\n", 1);
	return (0);
}
