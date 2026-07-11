public class GenCleanTailIndex014 {
    static int tail(int[] sizes) {
        return sizes[sizes.length - 1];
    }

    static boolean isEven1(int stock) {
        return stock % 2 == 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
