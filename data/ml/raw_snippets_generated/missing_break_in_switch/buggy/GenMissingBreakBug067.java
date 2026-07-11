public class GenMissingBreakBug067 {
    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int sum2(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "shipped";
            case 3:
                label = "closed";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static boolean isEven3(int limit) {
        return limit % 2 == 0;
    }

    static void printAll4(int[] ages) {
        for (int value : ages) {
            System.out.println(value);
        }
    }
}
