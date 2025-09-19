import { useEffect, useRef } from 'react';

interface UseInfiniteScrollOptions {
  threshold?: number; // どのくらい下部に近づいたら読み込むか（0-1）
  rootMargin?: string; // Intersection Observer のルートマージン
}

export function useInfiniteScroll(
  callback: () => void,
  isLoading: boolean,
  hasMore: boolean,
  options: UseInfiniteScrollOptions = {}
) {
  const { threshold = 0.1, rootMargin = '0px' } = options;
  const observerRef = useRef<IntersectionObserver | null>(null);
  const triggerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const trigger = triggerRef.current;
    if (!trigger) return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        // トリガー要素が見えて、読み込み中でない、かつまだ読み込むデータがある場合
        if (entry.isIntersecting && !isLoading && hasMore) {
          callback();
        }
      },
      {
        threshold,
        rootMargin,
      }
    );

    observerRef.current.observe(trigger);

    return () => {
      if (observerRef.current && trigger) {
        observerRef.current.unobserve(trigger);
      }
    };
  }, [callback, isLoading, hasMore, threshold, rootMargin]);

  return triggerRef;
}