public class GenCleanTailIndex022 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int largest2(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static int tail(int[] values) {
        return values[values.length - 1];
    }
}
