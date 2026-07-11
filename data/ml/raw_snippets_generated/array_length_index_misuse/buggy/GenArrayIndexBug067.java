public class GenArrayIndexBug067 {
    static int sum1(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static int sum2(int[] stocks) {
        int total = 0;
        for (int i = 0; i < stocks.length; i++) {
            total += stocks[i];
        }
        return total;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "queued";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static void showLast(int[] stocks) {
        System.out.println(stocks[stocks.length]);
    }
}
