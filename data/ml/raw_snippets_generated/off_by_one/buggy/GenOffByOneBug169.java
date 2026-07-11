public class GenOffByOneBug169 {
    static int addUp(int[] stocks) {
        int total = 0;
        for (int i = 0; i <= stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }
}
