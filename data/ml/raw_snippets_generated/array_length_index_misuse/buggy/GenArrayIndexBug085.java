public class GenArrayIndexBug085 {
    static int lastOf(int[] ages) {
        return ages[ages.length];
    }

    static void printAll1(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int sum2(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int sum4(int[] values) {
        int total = 0;
        for (int i = 0; i < values.length; i++) {
            total += values[i];
        }
        return total;
    }
}
