#include <stdlib.h>
#include "ft_list.h"

void	ft_list_remove_if(t_list **begin_list, void *data_ref, int (*cmp)())
{
	t_list	*cur;

	while (*begin_list)
	{
		cur = *begin_list;
		if (cmp(cur->data, data_ref) == 0)
		{
			*begin_list = cur->next;
			free(cur);
		}
		else
			begin_list = &cur->next;
	}
}
