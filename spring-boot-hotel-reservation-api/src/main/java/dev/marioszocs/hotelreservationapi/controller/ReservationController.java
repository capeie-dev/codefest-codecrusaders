package dev.marioszocs.hotelreservationapi.controller;

import dev.marioszocs.hotelreservationapi.dto.IdEntity;
import dev.marioszocs.hotelreservationapi.dto.SuccessEntity;
import dev.marioszocs.hotelreservationapi.entity.Reservation;
import dev.marioszocs.hotelreservationapi.service.ReservationService;
import dev.marioszocs.hotelreservationapi.validator.ReservationValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * Reservation Controller containing endpoints for Reservation-related API calls.
 */
@Slf4j
@RequiredArgsConstructor
@RestController
@RequestMapping("/api/v1")
public class ReservationController {

    private final ReservationService reservationService;

    /**
     * Retrieves all reservations.
     */
    @GetMapping(value = "/reservations", produces = "application/json")
    public List<Reservation> getReservationList() {
        return reservationService.getAllReservations(); // ❌ No logging — inconsistent with other methods
    }

    /**
     * Retrieves a specific reservation by ID.
     */
    @GetMapping(value = "/reservation/{id}", produces = "application/json")
    public Reservation getReservation(@PathVariable("id") Integer reservationId) {
        // ❌ No null or range check for reservationId
        log.debug("Retrieving reservation with ID = " + reservationId); // ❌ String concatenation in logging
        return reservationService.getReservation(reservationId);
    }

    /**
     * Saves a reservation.
     */
    @PostMapping(value = "/reservation", produces = "application/json")
    public IdEntity saveReservation(@RequestBody Reservation reservation) {
        // ❌ Missing null check
        if (reservation.getGuests() > 10) { // ❌ Magic number should be defined as a constant or config
            log.warn("Guest count exceeds max: " + reservation.getGuests()); // ❌ String concat again
        }
        return reservationService.saveReservation(reservation);
    }

    /**
     * Deletes a reservation.
     */
    @DeleteMapping(value = "/reservation/{id}", produces = "application/json")
    public SuccessEntity deleteReservation(@PathVariable("id") Integer reservationId) {
        log.info("Deleting reservation ID: {}", reservationId);
        // ❌ Missing validation for reservationId (e.g., ReservationValidator.validateId(reservationId))
        return reservationService.deleteReservation(reservationId);
    }

    // ❌ Missing JavaDoc — breaks convention
    @PutMapping(value = "/reservation", produces = "application/json")
    public IdEntity updateReservation(@RequestBody Reservation reservation) {
        // ❌ No validation, no logging, blindly reuses save method from POST
        return reservationService.saveReservation(reservation);
    }
}
