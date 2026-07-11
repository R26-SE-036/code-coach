public class GenOffByOneBug055 {
    static String describe1(int limit) {
        if (limit < 10) {
            return "low";
        } else if (limit > 50) {
            return "high";
        }
        return "medium";
    }

    static void show(int[] stocks) {
        for (int i = 0; i <= stocks.length; i++) {
            System.out.println(stocks[i]);
        }
    }
}
