public class GenCleanTailIndex012 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "archived";
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
                label = "final";
        }
        return label;
    }

    static int tail(int[] ratings) {
        return ratings[ratings.length - 1];
    }
}
