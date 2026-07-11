public class GenOffByOneBug136 {
    static int[] duplicate(int[] prices) {
        int[] copy = new int[prices.length];
        for (int i = 0; i <= prices.length; i++) {
            copy[i] = prices[i];
        }
        return copy;
    }

    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}
