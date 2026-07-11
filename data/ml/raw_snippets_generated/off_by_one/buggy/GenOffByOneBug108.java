public class GenOffByOneBug108 {
    static String describe1(int stock) {
        if (stock < 10) {
            return "low";
        } else if (stock > 50) {
            return "high";
        }
        return "medium";
    }

    static int addUp(int[] prices) {
        int total = 0;
        for (int i = 0; i <= prices.length; i++) {
            total += prices[i];
        }
        return total;
    }
}
