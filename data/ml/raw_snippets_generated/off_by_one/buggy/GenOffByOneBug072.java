public class GenOffByOneBug072 {
    static void show(int[] values) {
        for (int i = 0; i <= values.length; i++) {
            System.out.println(values[i]);
        }
    }

    static int largest1(int[] ratings) {
        int best = ratings[0];
        for (int i = 1; i < ratings.length; i++) {
            if (ratings[i] > best) {
                best = ratings[i];
            }
        }
        return best;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
