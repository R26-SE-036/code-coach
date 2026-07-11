public class GenCleanGeneric106 {
    static int drain1(int count) {
        int handled = 0;
        while (count > 0) {
            handled += count;
            count--;
        }
        return handled;
    }
}
