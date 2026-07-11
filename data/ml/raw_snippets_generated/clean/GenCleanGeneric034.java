public class GenCleanGeneric034 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static int drain2(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static void printAll3(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
    }
}
