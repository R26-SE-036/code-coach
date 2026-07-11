public class GenCleanGeneric109 {
    static int drain1(int points) {
        int handled = 0;
        while (points > 0) {
            handled += points;
            points--;
        }
        return handled;
    }
}
