public class GenOffByOneBug132 {
    static void show(int[] stocks) {
        for (int i = 0; i <= stocks.length; i++) {
            System.out.println(stocks[i]);
        }
    }
}
