public class GenOffByOneBug150 {
    static void show(int[] stocks) {
        for (int i = 0; i <= stocks.length; i++) {
            System.out.println(stocks[i]);
        }
    }

    static void printAll1(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
