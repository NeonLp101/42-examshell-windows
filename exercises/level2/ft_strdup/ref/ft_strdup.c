#include <stdlib.h>

char	*ft_strdup(char *src)
{
	char	*dup;
	int		len;

	len = 0;
	while (src[len])
		len++;
	dup = malloc(len + 1);
	if (!dup)
		return (NULL);
	dup[len] = '\0';
	while (len--)
		dup[len] = src[len];
	return (dup);
}
