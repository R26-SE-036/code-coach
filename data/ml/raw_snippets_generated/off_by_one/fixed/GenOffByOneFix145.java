public class GenOffByOneFix145 {
    static int[] duplicate(int[] stocks) {
        int[] copy = new int[stocks.length];
        for (int i = 0; i < stocks.length; i++) {
            copy[i] = stocks[i];
        }
        return copy;
    }
}
