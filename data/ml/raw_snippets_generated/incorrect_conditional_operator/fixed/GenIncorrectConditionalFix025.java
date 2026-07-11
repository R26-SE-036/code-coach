public class GenIncorrectConditionalFix025 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "shipped";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static void printAll2(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }

    static void printAll3(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int sum4(int[] prices) {
        int total = 0;
        for (int i = 0; i < prices.length; i++) {
            total += prices[i];
        }
        return total;
    }

    static String report(boolean done) {
        if (done == true) {
            return "active";
        }
        return "expired";
    }
}
