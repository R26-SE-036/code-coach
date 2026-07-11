public class GenCleanGeneric006 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static boolean isEven3(int budget) {
        return budget % 2 == 0;
    }

    static void printAll4(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static void printAll5(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }

    static int largest6(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }
}
