import { useQuery } from '@tanstack/react-query'
import { getResult, listResults } from '@/api/results'

export const useResults = () =>
  useQuery({
    queryKey: ['results'],
    queryFn: listResults,
  })

export const useResult = (id?: string) =>
  useQuery({
    queryKey: ['results', id],
    queryFn: () => getResult(id ?? ''),
    enabled: Boolean(id),
  })
